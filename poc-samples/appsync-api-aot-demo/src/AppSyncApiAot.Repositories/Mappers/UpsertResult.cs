using System.Text.Json.Serialization;

namespace AppSyncApiAot.Repositories.Mappers;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum UpsertResult
{
    Inserted,
    Updated,
}