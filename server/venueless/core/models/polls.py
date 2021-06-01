import uuid
from functools import cached_property

from django.db import models


class PollManager(models.Manager):
    def with_score(self):
        return self.get_queryset()  # TODO .annotate(_score=models.Count("votes"))


class Poll(models.Model):
    class States(models.TextChoices):
        DRAFT = "draft"
        OPEN = "open"
        CLOSED = "closed"
        ARCHIVED = "archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    content = models.TextField()
    state = models.CharField(
        default=States.DRAFT, choices=States.choices, max_length=10
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)
    cached_results = models.JSONField(null=True, blank=True)

    room = models.ForeignKey(
        to="Room",
        related_name="polls",
        on_delete=models.CASCADE,
    )

    objects = PollManager()

    @cached_property
    def results(self):
        # When the poll is retrieved with the with_results manager method,
        # we can just use the available score. We'll count manually otherwise.
        results = getattr(self, "_results", None)
        if results is not None:
            return results
        return self.get_results()

    def get_results(self):
        return  # TODO

    def serialize_public(self, answer_state=False):
        data = {
            "id": str(self.id),
            "content": self.content,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "room_id": str(self.room_id),
            "results": self.score or None,
            "is_pinned": self.is_pinned,
        }
        if answer_state:
            data["answer"] = getattr(self, "_answer", False)
        return data


class PollOption(models.Model):  # TODO/discuss: we can do without this model, too
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    content = models.TextField()


class PollVote(models.Model):
    option = models.ForeignKey(
        PollOption, on_delete=models.CASCADE, related_name="votes"
    )
    sender = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="poll_votes",
    )
