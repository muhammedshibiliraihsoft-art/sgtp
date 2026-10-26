from django.db import models


class WorkStatus(models.TextChoices):
    REQUEST = "REQUEST", "Request"
    CUTTING = "CUTTING", "Cutting"
    STITCHING = "STITCHING", "Stitching"
    CHECK = "CHECK", "Check"
    FINISHING = "FINISHING", "Finishing"
    QC = "QC", "Quality control"
    COMPLETED = "COMPLETED", "Completed"


class WorkPriority(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    URGENT = "URGENT", "Urgent"
    VERY_URGENT = "VERY_URGENT", "Very urgent"


NEXT_STATUS = {
    WorkStatus.REQUEST: WorkStatus.CUTTING,
    WorkStatus.CUTTING: WorkStatus.STITCHING,
    WorkStatus.STITCHING: WorkStatus.CHECK,
    WorkStatus.CHECK: WorkStatus.FINISHING,
    WorkStatus.FINISHING: WorkStatus.QC,
    WorkStatus.QC: WorkStatus.COMPLETED,
}

STAGE_FUNCTION = {
    WorkStatus.CUTTING: "CUTTING",
    WorkStatus.STITCHING: "STITCHING",
    WorkStatus.CHECK: "CHECK",
    WorkStatus.FINISHING: "FINISHING",
    WorkStatus.QC: "QC",
}
