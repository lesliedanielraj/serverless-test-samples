using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace AppSyncApiAot.Core.Models;

/// <summary>
/// The response object for Lambda functions handling request from AppSync proxy
/// </summary>
[DataContract]
public class AppSyncProxyRequest<TRequest>
{
    [DataMember(Name = "identity")]
    [JsonPropertyName("identity")]
    public string Identity { get; set; }

    [DataMember(Name = "result")]
    [JsonPropertyName("result")]
    public string Result { get; set; }
    
    [DataMember(Name = "error")]
    [JsonPropertyName("error")]
    public string Error { get; set; }

    [DataMember(Name = "prev")]
    [JsonPropertyName("prev")]
    public string Prev { get; set; }
    
    [DataMember(Name = "outErrors")]
    [JsonPropertyName("outErrors")]
    public List<string> OutErrors { get; set; }
    
    [DataMember(Name = "source")]
    [JsonPropertyName("source")]
    public string Source { get; set; }
    
    //Required
    
    [DataMember(Name = "request")]
    [JsonPropertyName("request")]
    public RequestContext Request { get; set; }

    [DataMember(Name = "info")]
    [JsonPropertyName("info")]
    public InfoContext Info { get; set; }

    /// <summary>
    /// Stash MUST be set and used for PIPELINE Resolvers
    /// </summary>
    [DataMember(Name = "stash")]
    [JsonPropertyName("stash")]
    public StashContext Stash { get; set; }

    [DataMember(Name = "arguments")]
    [JsonPropertyName("arguments")]
    public TRequest Arguments { get; set; }

    public class RequestContext
    {
        [DataMember(Name = "headers")]
        [JsonPropertyName("headers")]
        public IDictionary<string, string> Headers { get; set; }

        [DataMember(Name = "domainName")]
        [JsonPropertyName("domainName")]
        public string DomainName { get; set; }
    }

    public class InfoContext
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

    public class StashContext
    {
        [DataMember(Name = "headers")]
        [JsonPropertyName("headers")]
        public IDictionary<string, string> Headers { get; set; }

        [DataMember(Name = "info")]
        [JsonPropertyName("info")]
        public InfoContext Info { get; set; }
    }
}