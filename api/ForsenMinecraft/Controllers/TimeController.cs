using ForsenMinecraft.Dto;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class TimeController : ControllerBase
    {
        private readonly MainDatabaseContext dbContext;

        public TimeController(MainDatabaseContext dbContext)
        {
            this.dbContext = dbContext;
        }

        [HttpGet("latest")]
        public async Task<TimeEntry?> GetLatestAsync([BindRequired] string streamer)
        {
            DbTime? latest = await dbContext.Times.Where(t => t.IdStreamer == streamer).OrderByDescending(t => t.IdDate).FirstOrDefaultAsync();
            return latest == null ? null : TimeEntry.FromDbTime(latest);
        }

        [HttpGet("history")]
        public IActionResult GetHistoryAsync([BindRequired] string streamer, [BindRequired] DateTime from, [BindRequired] DateTime to)
        {
            if (to < from)
                return BadRequest("to date comes before from date");
            if (to - from > TimeSpan.FromDays(1))
                return BadRequest("timespan between from and to is too large");

            IQueryable<DbTime> results = dbContext.Times
                .Where(t => t.IdDate >= from && t.IdDate < to && t.IdStreamer == streamer)
                .OrderByDescending(t => t.IdDate)
                .AsNoTracking();

            return Ok(results.Select(t => TimeEntry.FromDbTime(t)));
        }
    }
}