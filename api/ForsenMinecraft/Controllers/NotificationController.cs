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
        private readonly MainDatabaseContext dbContext;

        public NotificationController(MainDatabaseContext dbContext)
        {
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
            if (notifyTimeEvents.TriggerMinutes.Any(t => t < 5 || t > 16))
            {
                return BadRequest("Trigger minutes must be between 5 and 16 minutes inclusive");
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
                dbContext.DbNotifyTimeEvents.Remove(timeEvent);
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
