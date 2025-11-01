import cors from "cors";
import dotenv from "dotenv";
import express from "express";

import connectDB from "./config/db";
import router from "./routes/index.route";

dotenv.config();
const PORT = process.env.PORT || 3000;

const app = express();
connectDB();

app.use(cors());
app.use(express.json());

app.use("/api", router);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
