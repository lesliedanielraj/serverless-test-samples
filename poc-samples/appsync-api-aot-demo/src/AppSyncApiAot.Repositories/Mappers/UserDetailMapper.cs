using Amazon.DynamoDBv2.Model;
using AppSyncApiAot.Repositories.Models;

namespace AppSyncApiAot.Repositories.Mappers;

public static class UserDetailMapper
{
    internal const string UserId = "user_id";
    internal const string FirstName = "first_name";
    internal const string LastName = "last_name";

    public static UserDetailDto ObjectFromDynamoDb(Dictionary<string, AttributeValue> items) =>
        new(items[UserId].S,
            items[FirstName].S,
            items[LastName].S);

    public static Dictionary<string, AttributeValue> ObjectToDynamoDb(UserDetailDto userDetail)
    {
        return new Dictionary<string, AttributeValue>(capacity: 1)
        {
            [UserId] = new(userDetail.UserId),
            [FirstName] = new(userDetail.FirstName),
            [LastName] = new(userDetail.LastName),
        };
    }
}