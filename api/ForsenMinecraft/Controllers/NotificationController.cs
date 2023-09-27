using ForsenMinecraft.Dto;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class NotificationController : ControllerBase
    {
        private readonly IConfiguration configuration;
        private readonly MainDatabaseContext dbContext;

        public NotificationController(IConfiguration configuration, MainDatabaseContext dbContext)
        {
            this.configuration = configuration;
            this.dbContext = dbContext;
        }

        [HttpPost("register")]
        public async Task RegisterAsync([BindRequired] PushSubscriptionInfo pushSubscription)
        {
            DbNotifyEndpoint? item = await dbContext.NotifyEndpoints.FirstOrDefaultAsync(e => e.UserId == pushSubscription.UserId);

            if (item == null)
            {
                dbContext.NotifyEndpoints.Add(new DbNotifyEndpoint()
                {
                    UserId = pushSubscription.UserId,
                    Endpoint = pushSubscription.Endpoint,
                    P256dh = pushSubscription.Keys.P256dh,
                    Auth = pushSubscription.Keys.Auth
                });
            }
            else
            {
                item.Endpoint = pushSubscription.Endpoint;
                item.P256dh = pushSubscription.Keys.P256dh;
                item.Auth = pushSubscription.Keys.Auth;
            }

            await dbContext.SaveChangesAsync();
        }

        [HttpPost("time_events")]
        public async Task<IActionResult> UpdateTimeEventsAsync([BindRequired] NotifyTimeEvents notifyTimeEvents)
        {
            if (notifyTimeEvents.TriggerMinutes.Any(t => t < configuration.GetValue<int>("TriggerMinuteMinimum") || t > configuration.GetValue<int>("TriggerMinuteMaximum")))
            {
                return BadRequest($"Trigger minutes must be between {configuration.GetValue<int>("TriggerMinuteMinimum")} and {configuration.GetValue<int>("TriggerMinuteMaximum")} minutes inclusive");
            }
            if (notifyTimeEvents.Streamer != "forsen" && notifyTimeEvents.Streamer != "xqc")
            {
                return BadRequest("Streamer must be forsen or xqc");
            }

            DbNotifyEndpoint? endpoint = await dbContext.NotifyEndpoints
                .Include(e => e.TimeEvents)
                .FirstOrDefaultAsync(e => e.UserId == notifyTimeEvents.UserId);

            if (endpoint == null)
            {
                return BadRequest("User ID not found. The endpoint must be registered first");
            }

            foreach (DbNotifyTimeEvent timeEvent in endpoint.TimeEvents
                .Where(e => e.Streamer == notifyTimeEvents.Streamer && Array.IndexOf(notifyTimeEvents.TriggerMinutes, e.TriggerTime.Minutes) < 0))
            {
                dbContext.NotifyTimeEvents.Remove(timeEvent);
            }

            foreach (TimeSpan newEvent in notifyTimeEvents.TriggerMinutes
                .Select(m => TimeSpan.FromMinutes(m))
                .Where(t => !endpoint.TimeEvents.Any(e => e.TriggerTime == t)))
            {
                endpoint.TimeEvents.Add(new DbNotifyTimeEvent()
                {
                    UserId = endpoint.UserId,
                    Streamer = notifyTimeEvents.Streamer,
                    TriggerTime = newEvent,
                    Endpoint = endpoint
                });
            }

            await dbContext.SaveChangesAsync();

            return Ok();
        }
    }
}
