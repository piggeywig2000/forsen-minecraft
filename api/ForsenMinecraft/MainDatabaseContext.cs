using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft
{
    public class MainDatabaseContext : DbContext
    {
        public MainDatabaseContext(DbContextOptions<MainDatabaseContext> options) : base(options) { }

        public DbSet<DbTime> Times { get; set; }
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
}
