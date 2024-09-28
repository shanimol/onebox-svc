/*
  Warnings:

  - Added the required column `task_id` to the `Calendar` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Calendar" ADD COLUMN     "task_id" TEXT NOT NULL;
