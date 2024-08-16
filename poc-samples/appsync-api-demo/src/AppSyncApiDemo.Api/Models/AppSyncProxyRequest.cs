using System.Runtime.Serialization;
using System.Text.Json.Serialization;

#nullable disable
namespace AppSyncApiDemo.Api.Models;

/// <summary>
/// The response object for Lambda functions handling request from AppSync proxy
/// </summary>
[DataContract]
public class AppSyncProxyRequest<TRequest>
{
    [DataMember(Name = "request")]
    [JsonPropertyName("request")]
    public Request Request { get; set; }
    
    [DataMember(Name = "info")]
    [JsonPropertyName("info")]
    public Info Info { get; set; }
    
    /// <summary>
    /// Stash MUST be set and used for PIPELINE Resolvers
    /// </summary>
    [DataMember(Name = "stash")]
    [JsonPropertyName("stash")]
    public Stash Stash { get; set; }
    
    [DataMember(Name = "arguments")]
    [JsonPropertyName("arguments")]
    public TRequest Arguments { get; set; }
}

[DataContract]
public class Request
{
    [DataMember(Name = "headers")]
    [JsonPropertyName("headers")]
    public IDictionary<string, string> Headers { get; set; }

    [DataMember(Name = "domainName")]
    [JsonPropertyName("domainName")]
    public object DomainName { get; set; }
}

[DataContract]
public class Info
{
    [DataMember(Name = "fieldName")]
    [JsonPropertyName("fieldName")]
    public string FieldName { get; set; }

    [DataMember(Name = "parentTypeName")]
    [JsonPropertyName("parentTypeName")]
    public string ParentTypeName { get; set; }

    [DataMember(Name = "variables")]
    [JsonPropertyName("variables")]
    public object Variables { get; set; }
}

[DataContract]
public class Stash
{
    [DataMember(Name = "headers")]
    [JsonPropertyName("headers")]
    public IDictionary<string, string> Headers { get; set; }

    [DataMember(Name = "info")]
    [JsonPropertyName("info")]
    public Info Info { get; set; }
}