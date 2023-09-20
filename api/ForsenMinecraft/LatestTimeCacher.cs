using System.Diagnostics;
using ForsenMinecraft.Dto;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft
{
    public class LatestTimeCacher
    {
        private static readonly SemaphoreSlim querySemaphore;
        private static readonly Stopwatch queryTimer;
        private static TimeEntry? lastResult;

        private readonly IConfiguration configuration;
        private readonly MainDatabaseContext dbContext;

        static LatestTimeCacher()
        {
            querySemaphore = new SemaphoreSlim(1);
            queryTimer = new Stopwatch();
            queryTimer.Start();
            lastResult = null;
        }

        public LatestTimeCacher(IConfiguration configuration, MainDatabaseContext dbContext)
        {
            this.configuration = configuration;
            this.dbContext = dbContext;
        }

        public async Task<TimeEntry?> GetLatestTime()
        {
            if (lastResult == null || queryTimer.Elapsed > TimeSpan.FromSeconds(configuration.GetValue<double>("TimeCacheSeconds")))
            {
                //Last result is stale, we need to refresh it
                try
                {
                    if (querySemaphore.Wait(0))
                    {
                        //This is the thread that performs the query
                        DbTime? latest = await dbContext.Times.OrderByDescending(t => t.IdDate).FirstOrDefaultAsync();
                        lastResult = latest == null ? null : TimeEntry.FromDbTime(latest);
                        queryTimer.Restart();
                    }
                    else
                    {
                        //Another thread is performing the query, we just need to wait
                        await querySemaphore.WaitAsync();
                    }
                }
                finally
                {
                    querySemaphore.Release();
                }
            }

            return lastResult;
        }
    }
}
