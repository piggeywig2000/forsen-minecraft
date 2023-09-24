namespace ForsenMinecraft.Dto
{
    public record PushSubscriptionInfo(Guid UserId, string Endpoint, PushSubscriptionInfoKeys Keys);
    public record PushSubscriptionInfoKeys(string P256dh, string Auth);
}
