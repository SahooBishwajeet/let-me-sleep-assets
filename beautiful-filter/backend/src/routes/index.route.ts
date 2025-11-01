import { Request, Response, Router } from "express";
import {
  createData,
  getAllData,
  getFilteredData,
} from "../controllers/data.controller";

const router = Router();

router.get("/", (req: Request, res: Response) => {
  res.status(200).send("API is running...");
});

router.get("/health", (req: Request, res: Response) => {
  res.status(200).json({ status: "OK", timestamp: new Date().toISOString() });
});

router.post("/data", createData);
router.get("/data", getAllData);
router.post("/data/filter", getFilteredData);

export default router;
