using Microsoft.Extensions.Configuration;

namespace AppSyncApiDemo.Repositories;

public class ApplicationConfigurationOptions
{
    [ConfigurationKeyName("PREFERENCE_TABLE_NAME")]
    public string PreferenceTableName { get; init; } = string.Empty;

    [ConfigurationKeyName("USER_DETAIL_TABLE_NAME")]
    public string UserDetailTableName { get; init; } = string.Empty;
}