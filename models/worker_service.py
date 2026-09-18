from extensions import db

class WorkerService(db.Model):
    __tablename__ = "worker_services"

    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    worker = db.relationship("Worker", back_populates="service_links")
    service = db.relationship("Service", back_populates="worker_links")

    __table_args__ = (
        db.UniqueConstraint("worker_id", "service_id", name="uq_worker_service"),
    )
