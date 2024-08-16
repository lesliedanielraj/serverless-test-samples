using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using AppSyncApiAot.Repositories.Models;

namespace AppSyncApiAot.Core.Models;

[DataContract]
public class UserDetail
{
    [DataMember(Name = "userId")]
    [JsonPropertyName("userId")]
    public string UserId { get; set; }

    [DataMember(Name = "firstName")]
    [JsonPropertyName("firstName")]
    public string FirstName { get; set; }

    [DataMember(Name = "lastName")]
    [JsonPropertyName("lastName")]
    public string LastName { get; set; }

    public UserDetailDto AsDto() => new(UserId, FirstName, LastName);
}