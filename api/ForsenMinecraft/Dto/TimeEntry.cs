namespace ForsenMinecraft.Dto
{
    public class TimeEntry
    {
        public DateTime Date { get; set; }
        public double Igt { get; set; }
        public double Rta { get; set; }

        public static TimeEntry FromDbTime(DbTime time) => new TimeEntry()
        {
            Date = time.IdDate,
            Igt = time.GameTime.TotalSeconds,
            Rta = time.RealTime.TotalSeconds
        };
    }
}
