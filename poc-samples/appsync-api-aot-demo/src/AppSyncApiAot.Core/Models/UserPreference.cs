using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using AppSyncApiAot.Repositories.Models;

namespace AppSyncApiAot.Core.Models;

[DataContract]
public class UserPreference
{
    [DataMember(Name = "userId")]
    [JsonPropertyName("userId")]
    public string UserId { get; set; }

    [DataMember(Name = "applicationKey")]
    [JsonPropertyName("applicationKey")]
    public Dictionary<string, string> ApplicationKey { get; set; }

    [DataMember(Name = "preference")]
    [JsonPropertyName("preference")]
    public object Preference { get; set; }

    public UserPreferenceDto AsDto() => new(UserId, ApplicationKey, Preference);
}