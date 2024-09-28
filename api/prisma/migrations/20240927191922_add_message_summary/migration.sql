-- CreateTable
CREATE TABLE "MessageSummary" (
    "id" TEXT NOT NULL DEFAULT (gen_random_uuid())::text,
    "message_id" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "MessageSummary_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "MessageSummary_id_key" ON "MessageSummary"("id");
