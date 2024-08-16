using Microsoft.Extensions.Options;

namespace AppSyncApiAot.Repositories;

public class ApplicationConfigurationsValidator : IValidateOptions<ApplicationConfigurationOptions>
{
    public ValidateOptionsResult Validate(string? name, ApplicationConfigurationOptions options)
    {
        if (name != Options.DefaultName) return ValidateOptionsResult.Skip;
        
        if (string.IsNullOrEmpty(options.PreferenceTableName))
        {
            ValidateOptionsResult.Fail("Unable to load setting CONNECTION_TABLE_NAME");
        }
        
        if (string.IsNullOrEmpty(options.UserDetailTableName))
        {
            ValidateOptionsResult.Fail("Unable to load setting USER_DETAIL_TABLE_NAME");
        }

        return ValidateOptionsResult.Success;
    }
}