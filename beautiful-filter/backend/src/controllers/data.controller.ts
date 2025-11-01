import { Request, Response } from "express";
import DataModel from "../models/data.model";
import {
  buildMongoQuery,
  FieldTypeMap,
  FilterCondition,
} from "../utils/filter";

export const createData = async (
  req: Request,
  res: Response
): Promise<void> => {
  try {
    const { name, email, dateOfBirth, score, isPriority } = req.body;
    if (!name || !email) {
      res.status(400).json({ message: "Missing required fields" });
      return;
    }

    const data = await DataModel.create({
      name: name,
      email: email,
      dateOfBirth: new Date(dateOfBirth),
      score: score,
      isPriority: isPriority,
    });

    res.status(201).json({
      message: "Data created successfully",
      data: data,
    });
  } catch (error) {
    res.status(500).json({ message: "Internal server error" });
  }
};

export const getAllData = async (
  req: Request,
  res: Response
): Promise<void> => {
  try {
    const data = await DataModel.find().select("-__v -_id");
    res.status(200).json({
      message: "Data retrieved successfully",
      data: data,
    });
  } catch (error) {
    res.status(500).json({ message: "Internal server error" });
  }
};

export const getFilteredData = async (
  req: Request,
  res: Response
): Promise<void> => {
  try {
    const { filters }: { filters: FilterCondition[] } = req.body || {};
    const fieldTypeMap: FieldTypeMap = {
      name: "array",
      email: "string",
      dateOfBirth: "date",
      score: "number",
      isPriority: "boolean",
      createdAt: "date",
      updatedAt: "date",
    };

    const { query, error } = buildMongoQuery(filters, fieldTypeMap);

    if (error) {
      res
        .status(400)
        .json({ message: "Invalid filter conditions", error: error.message });
      return;
    }

    const data = await DataModel.find(query || {}).select("-__v -_id");

    res.status(200).json({
      message: `${data.length} filtered data retrieved successfully`,
      data: data,
    });
  } catch (error) {
    console.error("Error in getFilteredData:", error);
    res.status(500).json({ message: "Internal server error" });
  }
};
