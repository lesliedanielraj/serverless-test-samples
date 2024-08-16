using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Amazon.DynamoDBv2;
using Amazon.XRay.Recorder.Handlers.AwsSdk;
using AppSyncApiDemo.Repositories;
using AppSyncApiDemo.Repositories.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Options;

namespace AppSyncApiDemo.Infrastructure;

public static class Startup
{
    private static IServiceProvider _serviceProvider;

    public static IServiceProvider ServiceProvider => _serviceProvider ??= InitializeServiceProvider();

    private static void AddDefaultServices(IServiceCollection services)
    {
        AWSSDKHandler.RegisterXRayForAllServices();
        var builder = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddInMemoryCollection(
                new Dictionary<string, string>()
                {
                    ["PREFERENCE_TABLE_NAME"] = "Preferences",
                    ["USER_DETAIL_TABLE_NAME"] = "UserDetails",
                }!)
            .AddEnvironmentVariables();

        IConfiguration configuration = builder.Build();

        services.Configure<ApplicationConfigurationOptions>(configuration);
        services.TryAddSingleton(configuration);
        services.TryAddSingleton(static _ =>
            Options.Create(new JsonSerializerOptions
            {
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            }));
        services
            .TryAddTransient<IValidateOptions<ApplicationConfigurationOptions>, ApplicationConfigurationsValidator>();

        services.TryAddSingleton<IAmazonDynamoDB>(static _ => new AmazonDynamoDBClient());
        services.TryAddSingleton<IDynamoDbRepository<UserPreferenceDto>, UserPreferenceRepository>();
        services.TryAddSingleton<IDynamoDbRepository<UserDetailDto>, UserDetailRepository>();
    }

    private static IServiceProvider InitializeServiceProvider()
    {
        var services = new ServiceCollection();
        AddDefaultServices(services);
        return services.BuildServiceProvider();
    }
}