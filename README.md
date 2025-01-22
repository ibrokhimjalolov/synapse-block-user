
# Block User Module Documentation

The **Block User Module** is a Matrix Synapse extension that enables users to block and unblock other users, while enforcing rules and providing features related to blocking, event handling, and spam checking. This module includes the following capabilities:

- **Blocking and Unblocking Users**: Users can manage blocked users via the account data API.
- **Web Resource for Block Management**: Exposes an API endpoint to manage and query blocked users.
- **Private Room Handling**: Ensures that blocked users cannot interact in private rooms.
- **Spam Prevention**: Prevents sending messages or invitations in cases where users are blocked.

---

### Key Features

#### 1. **Blocking and Unblocking Users**

- Users can block/unblock others, and the blocked list is synced using Synapse's account data API.
- When users are added or removed from the blocked list, their blocked status is checked in the context of rooms they share.
  
#### 2. **Web Resource for Block Management**
The module exposes a REST API that allows clients to interact with the blocking functionality:

- **API Endpoint**: `/_synapse/client/v3/block_user`
- **Resource**: `BlockUserResource`
  - **BlockUserInfoResource**: Retrieves information about whether a user has blocked another user, and whether a user is blocked.
  - **BlockedUserListResource**: Retrieves a list of blocked users for a specific user.

#### 3. **Private Room and Presence Management**
The module ensures that if a user blocks another user, they cannot invite or communicate with each other in private rooms.

- **Invitations**: The module checks if a user trying to invite another is blocked. If blocked, the invitation is rejected.
- **Spam Checking**: The module checks if an event, like a message, should be considered spam if it is sent by a user who is blocked by another.
