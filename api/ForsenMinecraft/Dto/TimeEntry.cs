namespace ForsenMinecraft.Dto
{
    public record TimeEntry(DateTime Date, double Igt, double Rta)
    {
        public static TimeEntry FromDbTime(DbTime time) => new TimeEntry(time.IdDate, time.GameTime.TotalSeconds, time.RealTime.TotalSeconds);
    }
}
