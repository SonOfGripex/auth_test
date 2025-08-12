from tortoise import fields
from datetime import datetime
from app.core.base_model import BaseModel
import uuid

class User(BaseModel):
    uuid = fields.UUIDField(default=uuid.uuid4, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255, null=True)

    roles = fields.ManyToManyField(
        "models.Role",
        through="user_role",
        forward_key="user_id",
        backward_key="role_id",
        related_name="users"
    )

    permissions = fields.ManyToManyField(
        "models.Permission",
        through="user_permission",
        forward_key="user_id",
        backward_key="permission_id",
        related_name="users"
    )

    class Meta:
        table = "users"

    def __str__(self):
        return self.username


class Role(BaseModel):
    name = fields.CharField(max_length=100, unique=True)

    permissions: fields.ManyToManyRelation["Permission"] = fields.ManyToManyField(
        "models.Permission",
        through="rolepermission",
        forward_key="role_id",
        backward_key="permission_id",
        related_name="roles"
    )

    class Meta:
        table = "roles"

    def __str__(self):
        return self.name


class Permission(BaseModel):
    name = fields.CharField(max_length=100, unique=True)

    class Meta:
        table = "permissions"

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="user_roles")
    role = fields.ForeignKeyField("models.Role", related_name="role_users")

    class Meta:
        table = "user_role"
        unique_together = ("user", "role")


class UserPermission(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="user_permissions")
    permission = fields.ForeignKeyField("models.Permission", related_name="permission_users")

    class Meta:
        table = "user_permission"
        unique_together = ("user", "permission")


class RolePermission(BaseModel):
    role = fields.ForeignKeyField("models.Role", related_name="role_permissions")
    permission = fields.ForeignKeyField("models.Permission", related_name="permission_roles")

    class Meta:
        table = "role_permission"
        unique_together = ("role", "permission")


class RefreshToken(BaseModel):
    uuid = fields.UUIDField(default=uuid.uuid4, unique=True)
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens", on_delete=fields.CASCADE)
    token_hash = fields.CharField(max_length=256, unique=True)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    revoked = fields.BooleanField(default=False)

    class Meta:
        table = "refresh_tokens"

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)