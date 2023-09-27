using Microsoft.AspNetCore.HttpOverrides;
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
            if (builder.Environment.IsDevelopment())
            {
                builder.Services.AddCors(options => options.AddDefaultPolicy(policy => policy
                    .AllowAnyOrigin()
                    .AllowAnyHeader()));
            }

            string mainDbReadWriteConnectionString = builder.Configuration.GetConnectionString("MainDbReadWrite") ?? throw new ArgumentNullException("MainDbReadWrite", "Main database connection string was not found in the configuration");
            builder.Services.AddDbContext<MainDatabaseContext>(contextOptions => contextOptions
                .UseMySql(mainDbReadWriteConnectionString, ServerVersion.AutoDetect(mainDbReadWriteConnectionString)));

            builder.Services.AddHostedService<NotificationTriggerService>();

            builder.Services.AddControllers();

            var app = builder.Build();

            // Configure the HTTP request pipeline.
            if (app.Environment.IsProduction())
            {
                app.UseForwardedHeaders(new ForwardedHeadersOptions
                {
                    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto
                });
            }

            if (app.Environment.IsDevelopment())
            {
                app.UseHttpsRedirection();
                app.UseCors();
            }

            app.UseAuthorization();


            app.MapControllers();

            app.Run();
        }
    }
}