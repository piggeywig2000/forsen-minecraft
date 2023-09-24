using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft
{
    public class MainDatabaseContext : DbContext
    {
        public MainDatabaseContext(DbContextOptions<MainDatabaseContext> options) : base(options) { }

        public DbSet<DbTime> Times { get; set; }
        public DbSet<DbNotifyEndpoint> NotifyEndpoints { get; set; }
        public DbSet<DbNotifyTimeEvent> DbNotifyTimeEvents { get; set; }

        //protected override void OnModelCreating(ModelBuilder modelBuilder)
        //{
        //    modelBuilder.Entity<DbNotifyEndpoint>()
        //        .HasMany(e => e.TimeEvents)
        //        .WithOne(e => e.Endpoint)
        //        .HasForeignKey(e => e.UserId);
        //}
    }

    [Table("times")]
    [PrimaryKey(nameof(IdDate), nameof(IdStreamer))]
    public class DbTime
    {
        [Column("id_date")]
        public DateTime IdDate { get; set; }

        [Column("id_streamer")]
        public required string IdStreamer { get; set; }

        [Column("game_time")]
        public TimeSpan GameTime { get; set; }

        [Column("real_time")]
        public TimeSpan RealTime { get; set; }
    }

    [Table("notify_endpoints")]
    public class DbNotifyEndpoint
    {
        [Key]
        [Column("user_id")]
        public required Guid UserId { get; set; }

        [Column("endpoint")]
        public required string Endpoint { get; set; }

        [Column("p256dh")]
        public required string P256dh { get; set; }

        [Column("auth")]
        public required string Auth { get; set; }

        public ICollection<DbNotifyTimeEvent> TimeEvents { get; } = null!;
    }

    [Table("notify_time_events")]
    public class DbNotifyTimeEvent
    {
        [Key]
        [Column("id")]
        public uint Id { get; set; }

        [Column("user_id")]
        public required Guid UserId { get; set; }

        [Column("trigger_time")]
        public TimeSpan TriggerTime { get; set; }

        [ForeignKey(nameof(UserId))]
        public required DbNotifyEndpoint Endpoint { get; set; }
    }
}
