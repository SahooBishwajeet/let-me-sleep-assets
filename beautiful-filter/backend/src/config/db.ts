import mongoose from "mongoose";

const connectDB = async () => {
  try {
    const dbUrl = process.env.MONGODB_URI;

    if (!dbUrl) {
      throw new Error("MONGODB_URI is not defined in environment variables");
    }

    await mongoose.connect(dbUrl);
    console.log("MongoDB connected");
  } catch (error) {
    console.error("MongoDB connection error:", error);
    process.exit(1);
  }
};

export default connectDB;
