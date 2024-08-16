using System.Text.Json.Serialization;

namespace AppSyncApiAot.Infrastructure;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum RequestType
{
    Querystring,
    Path,
    Body,
    None
}