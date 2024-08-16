using System.Text.Json;
using Amazon.DynamoDBv2.Model;
using AppSyncApiAot.Repositories.Models;

namespace AppSyncApiAot.Repositories.Mappers;

public static class UserPreferenceMapper
{
    internal const string UserId = "user_id";
    internal const string ApplicationKey = "application_key";
    internal const string Preference = "preference";

    public static UserPreferenceDto ObjectFromDynamoDb(Dictionary<string, AttributeValue> items) =>
        new(items[UserId].S,
            items[ApplicationKey].S.Split("#")
                .Select(x => new KeyValuePair<string, string>(x.Split(":")[0], x.Split(":")[1]))
                .ToDictionary(),
            JsonSerializer.Deserialize<object>(items[Preference].S) ?? "{}");

    public static Dictionary<string, AttributeValue> ObjectToDynamoDb(UserPreferenceDto userPreference)
    {
        return new Dictionary<string, AttributeValue>(capacity: 1)
        {
            [UserId] = new(userPreference.UserId),
            [ApplicationKey] = new(userPreference.SortKey),
            [Preference] = new()
            {
                S = JsonSerializer.Serialize(userPreference.Preference)
            }
        };
    }
}