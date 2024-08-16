namespace AppSyncApiDemo.Repositories.Models;

public record UserDetailDto(string UserId, string FirstName, string LastName)
{
    public string UserId { get; } = UserId;
    public string FirstName { get; } = FirstName;
    public string LastName { get; } = LastName;
}