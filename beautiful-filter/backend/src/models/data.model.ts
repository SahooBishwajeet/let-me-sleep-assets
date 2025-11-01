import { Document, model, Schema } from "mongoose";

export interface IData extends Document {
  id: string;
  name: string;
  email: string;
  dateOfBirth?: Date;
  score?: number;
  isPriority?: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const DataSchema: Schema = new Schema(
  {
    id: {
      type: String,
      default: () => crypto.randomUUID(),
      unique: true,
    },
    name: {
      type: String,
      required: true,
    },
    email: {
      type: String,
      required: true,
    },
    dateOfBirth: {
      type: Date,
    },
    score: {
      type: Number,
    },
    isPriority: {
      type: Boolean,
    },
  },
  {
    timestamps: true,
  }
);

const DataModel = model<IData>("Data", DataSchema);
export default DataModel;
