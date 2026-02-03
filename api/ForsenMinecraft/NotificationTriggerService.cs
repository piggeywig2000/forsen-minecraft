using System.Diagnostics;
using System.Net;
using System.Text.Json;
using ForsenMinecraft.Dto;
using Lib.Net.Http.WebPush;
using Lib.Net.Http.WebPush.Authentication;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft
{
    public class NotificationTriggerService : BackgroundService
    {
        private readonly ILogger<NotificationTriggerService> logger;
        private readonly IConfiguration configuration;
        private readonly IServiceScopeFactory serviceScopeFactory;

        private readonly TimeSpan POLL_INTERVAL = TimeSpan.FromSeconds(4);
        private readonly VapidAuthentication vapidAuth;
        private readonly PushServiceClient webPushClient;

        public NotificationTriggerService(ILogger<NotificationTriggerService> logger, IConfiguration configuration, IServiceScopeFactory serviceScopeFactory, PushServiceClient webPushClient)
        {
            this.logger = logger;
            this.configuration = configuration;
            this.serviceScopeFactory = serviceScopeFactory;
            this.webPushClient = webPushClient;

            vapidAuth = new VapidAuthentication(configuration.GetValue<string>("Vapid:PublicKey"), configuration.GetValue<string>("Vapid:PrivateKey"));
            vapidAuth.Subject = configuration.GetValue<string>("Vapid:Subject");
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            Stopwatch stopwatch = Stopwatch.StartNew();
            TimeSpan targetTime = TimeSpan.FromSeconds(0);
            Dictionary<string, TimeSpan?> lastTimerValue = new Dictionary<string, TimeSpan?>()
            {
                { "forsen", null },
                { "xqc", null }
            };

            while (!stoppingToken.IsCancellationRequested)
            {
                targetTime += POLL_INTERVAL;

                IServiceScope serviceScope = serviceScopeFactory.CreateScope();
                MainDatabaseContext dbContext = serviceScope.ServiceProvider.GetRequiredService<MainDatabaseContext>();

                Dictionary<string, (TimeSpan, TimeSpan, DateTimeOffset)> streamerToTime = new Dictionary<string, (TimeSpan, TimeSpan, DateTimeOffset)>();

                foreach (string streamer in lastTimerValue.Keys)
                {
                    DbTime? latestTimeEntry = await dbContext.Times
                        .AsNoTracking()
                        .Where(t => t.IdStreamer == streamer)
                        .OrderByDescending(t => t.IdDate)
                        .FirstOrDefaultAsync(stoppingToken);

                    //If there are no times, skip
                    if (latestTimeEntry == null)
                        continue;

                    TimeSpan currentTime = latestTimeEntry.GameTime;
                    TimeSpan? previousTime = lastTimerValue[streamer];
                    lastTimerValue[streamer] = currentTime;

                    if (previousTime == null)
                        continue;

                    //If current time is lower than previous, he reset
                    if (currentTime <= previousTime)
                        continue;

                    //If the time difference is more than 2 minutes, he probably loaded an old world
                    if (currentTime - previousTime > TimeSpan.FromMinutes(2))
                        continue;

                    //If we didn't cross a minute boundary in the valid time range, skip
                    if (currentTime.Minutes <= previousTime.Value.Minutes ||
                        currentTime.Minutes < configuration.GetValue<int>("TriggerMinuteMinimum") ||
                        currentTime.Minutes > configuration.GetValue<int>("TriggerMinuteMaximum"))
                        continue;

                    //Add to dictionary to process later
                    DateTimeOffset timestamp = new DateTimeOffset(latestTimeEntry.IdDate, TimeSpan.Zero);
                    streamerToTime[streamer] = (currentTime, previousTime.Value, timestamp);
                }

                if (streamerToTime.Count > 0)
                {
                    //Start processing dictionary (fire and forget)
                    _ = SendNotifications(serviceScope, dbContext, streamerToTime, stoppingToken);
                }
                else
                {
                    serviceScope.Dispose();
                }

                if (stopwatch.Elapsed < targetTime)
                    await Task.Delay(targetTime - stopwatch.Elapsed, stoppingToken); //Wait for the target
                else
                    targetTime = stopwatch.Elapsed; //Missed the target so reset the target
            }
        }

        private async Task SendNotifications(IServiceScope serviceScope, MainDatabaseContext dbContext, Dictionary<string, (TimeSpan currentTime, TimeSpan previousTime, DateTimeOffset timestamp)> streamerToTime, CancellationToken stoppingToken)
        {
            try
            {
                Stopwatch stopwatch = new Stopwatch();

                foreach (string streamer in streamerToTime.Keys)
                {
                    (TimeSpan currentTime, TimeSpan previousTime, DateTimeOffset timestamp) = streamerToTime[streamer];
                    logger.Log(LogLevel.Information, "Begin send notifications for {streamer} at {time} minutes", streamer, currentTime.Minutes);
                    stopwatch.Restart();

                    string payload = JsonSerializer.Serialize(new NotifyPayload(streamer, currentTime.Minutes, timestamp), new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

                    //Send out notifications
                    await Parallel.ForEachAsync(dbContext.NotifyTimeEvents
                        .Where(e => e.Streamer == streamer && e.TriggerTime >= previousTime && e.TriggerTime <= currentTime)
                        .Include(e => e.Endpoint)
                        .AsAsyncEnumerable(), new ParallelOptions()
                        {
                            MaxDegreeOfParallelism = 16,
                            CancellationToken = stoppingToken
                        },
                        async (timeEvent, stoppingToken) =>
                        {
                            PushSubscription pushSubscription = new PushSubscription();
                            pushSubscription.Endpoint = timeEvent.Endpoint.Endpoint;
                            pushSubscription.SetKey(PushEncryptionKeyName.P256DH, timeEvent.Endpoint.P256dh);
                            pushSubscription.SetKey(PushEncryptionKeyName.Auth, timeEvent.Endpoint.Auth);

                            try
                            {
                                await webPushClient.RequestPushMessageDeliveryAsync(pushSubscription, new PushMessage(payload), vapidAuth, VapidAuthenticationScheme.Vapid, stoppingToken);
                            }
                            catch (PushServiceClientException e)
                            {
                                if (e.StatusCode == HttpStatusCode.NotFound || e.StatusCode == HttpStatusCode.Gone)
                                {
                                    dbContext.NotifyEndpoints.Remove(timeEvent.Endpoint);
                                    logger.Log(LogLevel.Information, "Removing endpoint {id} because it expired", timeEvent.Endpoint.UserId);
                                }
                                else
                                    throw;
                            }
                        });

                    logger.Log(LogLevel.Information, "Finish send notifications for {streamer} at {time} minutes. Took {duration}ms", streamer, currentTime.Minutes, stopwatch.ElapsedMilliseconds);
                }

                await dbContext.SaveChangesAsync(stoppingToken);
            }
            finally
            {
                serviceScope.Dispose();
            }
        }
    }
}
