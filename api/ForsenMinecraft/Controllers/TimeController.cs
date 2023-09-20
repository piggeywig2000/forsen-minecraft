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
        private readonly LatestTimeCacher latestTimeCacher;

        public TimeController(MainDatabaseContext dbContext, LatestTimeCacher latestTimeCacher)
        {
            this.dbContext = dbContext;
            this.latestTimeCacher = latestTimeCacher;
        }

        [HttpGet("latest")]
        public Task<TimeEntry?> GetLatestAsync()
        {
            return latestTimeCacher.GetLatestTime();
        }

        [HttpGet("history")]
        public IActionResult GetHistoryAsync([BindRequired] DateTime from, [BindRequired] DateTime to)
        {
            if (to < from)
                return BadRequest("to date comes before from date");
            if (to - from > TimeSpan.FromDays(1))
                return BadRequest("timespan between from and to is too large");

            IQueryable<DbTime> results = dbContext.Times
                .Where(t => t.IdDate >= from && t.IdDate < to)
                .OrderByDescending(t => t.IdDate)
                .AsNoTracking();

            return Ok(results.Select(t => TimeEntry.FromDbTime(t)));
        }
    }
}