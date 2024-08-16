namespace AppSyncApiAot.Repositories.Models;

public record UserPreferenceDto(string UserId, Dictionary<string, string> ApplicationKey, object Preference)
{
    public string UserId { get; } = UserId;
    public Dictionary<string, string> ApplicationKey { get; } = ApplicationKey;
    public object Preference { get; } = Preference;

    public readonly string SortKey = string.Join("#", ApplicationKey
        .Select(x => string.Concat(x.Key, ":", x.Value)));
}