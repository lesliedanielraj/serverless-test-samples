using System.Text.Json.Serialization;

namespace AppSyncApiDemo.Infrastructure;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum RequestType
{
    Querystring,
    Path,
    Body,
    None
}