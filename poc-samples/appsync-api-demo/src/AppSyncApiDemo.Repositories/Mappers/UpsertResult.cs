using System.Text.Json.Serialization;

namespace AppSyncApiDemo.Repositories.Mappers;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum UpsertResult
{
    Inserted,
    Updated,
}