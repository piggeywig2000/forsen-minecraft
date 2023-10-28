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
        public Task<TimeEntry?> GetLatestAsync([BindRequired] string streamer)
        {
            return dbContext.Times
                .AsNoTracking()
                .Where(t => t.IdStreamer == streamer)
                .OrderByDescending(t => t.IdDate)
                .Select(t => t == null ? null : TimeEntry.FromDbTime(t))
                .FirstOrDefaultAsync();
        }

        [HttpGet("history")]
        public IActionResult GetHistoryAsync([BindRequired] string streamer, [BindRequired] DateTime from, [BindRequired] DateTime to)
        {
            if (to < from)
                return BadRequest("To date comes before from date");
            if (to - from > TimeSpan.FromHours(25.5))
                return BadRequest("Timespan between from and to is too large");

            IQueryable<DbTime> results = dbContext.Times
                .AsNoTracking()
                .Where(t => t.IdDate >= from && t.IdDate < to && t.IdStreamer == streamer)
                .OrderByDescending(t => t.IdDate);

            return Ok(results.Select(t => TimeEntry.FromDbTime(t)));
        }
    }
}