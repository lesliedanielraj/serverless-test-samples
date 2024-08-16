using Amazon.SecretsManager;
using Amazon.SecretsManager.Model;

namespace AppSyncApiDemo.Repositories.Helpers;

public static class SecretsManagerHelper
{
    public static async Task<string> GetSecretValue(string secretName)
    {
        var client = new AmazonSecretsManagerClient();

        var request = new GetSecretValueRequest
        {
            SecretId = secretName,
        };

        var response = await client.GetSecretValueAsync(request);
        return response.SecretString;
    }
}