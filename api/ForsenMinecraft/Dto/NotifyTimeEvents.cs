namespace ForsenMinecraft.Dto
{
    public record NotifyTimeEvents(Guid UserId, string Streamer, int[] TriggerMinutes);
}
