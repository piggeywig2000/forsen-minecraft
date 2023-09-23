using Microsoft.EntityFrameworkCore;

namespace ForsenMinecraft
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            builder.Configuration.AddJsonFile("appsettings.Private.json");

            // Add services to the container.
            string mainDbConnectionString = builder.Configuration.GetConnectionString("MainDbRead") ?? throw new ArgumentNullException("MainDbRead", "Main database connection string was not found in the configuration");
            builder.Services.AddDbContext<MainDatabaseContext>(contextOptions => contextOptions
                .UseMySql(mainDbConnectionString, ServerVersion.AutoDetect(mainDbConnectionString)));
            builder.Services.AddControllers();

            var app = builder.Build();

            // Configure the HTTP request pipeline.

            app.UseAuthorization();


            app.MapControllers();

            app.Run();
        }
    }
}