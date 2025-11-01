import { FilterQuery } from "mongoose";

export class InvalidFilterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidFilterError";
  }
}

export interface FilterBuilderResult {
  query: FilterQuery<any> | null;
  error: InvalidFilterError | null;
}

export interface FilterCondition {
  id: string;
  field: string;
  operator: string;
  values: any[];
}

export interface FieldTypeMap {
  [fieldName: string]: "string" | "number" | "date" | "boolean" | "array";
}

function escapeRegExp(str: string): string {
  if (str == null) return "";
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const isValueValid = (val: any) =>
  val !== null && val !== undefined && val !== "";

/**
 * Validates and transforms a client-side filter array into a MongoDB query object.
 *
 * @param {FilterCondition[]} filters - An array of filter objects from the client.
 * @param {FieldTypeMap} [typeMap={}] - A map of field names to their data types
 * (e.g., `{ dateOfBirth: 'date', score: 'number' }`). This is crucial for
 * applying type-specific logic.
 *
 * @returns {FilterBuilderResult} An object containing either:
 * - `query`: The compiled Mongoose `FilterQuery` (or `{}` if no filters).
 * - `error`: An `InvalidFilterError` object if any filter is invalid.
 *
 * @example
 * // --- Full Usage Example (e.g., in an Express controller) ---
 *
 * import { Request, Response } from 'express';
 * import DataModel from '@/models/DataModel';
 * import {
 *    buildMongoQuery,
 *    FilterCondition,
 *    FieldTypeMap
 * } from '@/utils/filterBuilder';
 *
 * // 1. Define the type map for your model
 * const myFieldTypes: FieldTypeMap = {
 *   name: 'string',
 *   email: 'string',
 *   dateOfBirth: 'date',
 *   score: 'number',
 *   isPriority: 'boolean',
 *   createdAt: 'date',
 * };
 *
 * export const getFilteredData = async (req: Request, res: Response) => {
 *   try {
 *     const { filters }: { filters: FilterCondition[] } = req.body || {};
 *
 *     // 2. Build and validate the query
 *     const { query, error } = buildMongoQuery(filters, myFieldTypes);
 *
 *     // 3. Handle validation errors
 *     if (error) {
 *       // Send a 400 Bad Request to the client
 *       return res.status(400).json({
 *         message: "Invalid filter condition.",
 *         error: error.message,
 *       });
 *     }
 *
 *     // 4. Use the valid query
 *     const data = await DataModel.find(query || {});
 *
 *     res.status(200).json({
 *       message: "Data retrieved successfully.",
 *       query: query, // Optional: return the query for debugging
 *       data: data,
 *     });
 *
 *   } catch (dbError) {
 *      // 5. Handle 500-level server errors (e.g., database down)
 *      res.status(500).json({ message: "Internal server error." });
 *   }
 * };
 */
export const buildMongoQuery = (
  filters: FilterCondition[],
  typeMap: FieldTypeMap = {}
): FilterBuilderResult => {
  if (!filters || filters.length === 0) {
    return { query: {}, error: null };
  }

  const queryParts = [];

  for (const filter of filters) {
    const { field, operator, values } = filter;
    const [value, value2] = values;
    const fieldType = typeMap[field];

    if (
      !["empty", "not_empty"].includes(operator) &&
      (!values || values.length === 0)
    ) {
      return {
        query: null,
        error: new InvalidFilterError(
          `Filter for field '${field}' is missing 'values' array.`
        ),
      };
    }

    try {
      switch (operator) {
        // --- 'is' Operator (For text, date, boolean, select, etc.) ---
        case "is": {
          if (fieldType === "date") {
            if (!isValueValid(value))
              throw new Error("A valid date value is required.");

            const startDate = new Date(value);
            startDate.setHours(0, 0, 0, 0);
            const endDate = new Date(value);
            endDate.setHours(23, 59, 59, 999);

            if (isNaN(startDate.getTime()))
              throw new Error("Invalid date format provided.");

            // Logic: "is between the start and end of the day"
            queryParts.push({ [field]: { $gte: startDate, $lte: endDate } });
          } else {
            queryParts.push({ [field]: { $eq: value } });
          }
          break;
        }

        // --- 'between' Operator (For numbers and dates) ---
        case "between": {
          if (!isValueValid(value) || !isValueValid(value2)) {
            throw new Error("Operator 'between' requires two valid values.");
          }

          if (fieldType === "number") {
            queryParts.push({
              [field]: { $gte: Number(value), $lte: Number(value2) },
            });
          } else if (fieldType === "array") {
            // For 'numberrange' type
            // Assumes field is stored as [min, max] (e.g., [10, 50])
            // Logic: storedMin >= value AND storedMax <= value2
            queryParts.push({
              $and: [
                { [`${field}.0`]: { $gte: Number(value) } },
                { [`${field}.1`]: { $lte: Number(value2) } },
              ],
            });
          } else {
            const startDate = new Date(value);
            const endDate = new Date(value2);
            if (isNaN(startDate.getTime()) || isNaN(endDate.getTime()))
              throw new Error("Invalid date format provided for 'between'.");

            queryParts.push({ [field]: { $gte: startDate, $lte: endDate } });
          }
          break;
        }

        // --- 'not_between' Operator (For dates only ) ---
        case "not_between": {
          if (!isValueValid(value) || !isValueValid(value2)) {
            throw new Error(
              "Operator 'not_between' requires two valid values."
            );
          }

          // Assumes 'date' or 'datetime' type
          const startDate = new Date(value);
          const endDate = new Date(value2);
          if (isNaN(startDate.getTime()) || isNaN(endDate.getTime()))
            throw new Error("Invalid date format provided for 'not_between'.");

          // Logic: "is before the start date OR after the end date"
          queryParts.push({
            $or: [
              { [field]: { $lt: startDate } },
              { [field]: { $gt: endDate } },
            ],
          });
          break;
        }

        // --- 'overlaps' Operator (For array ranges only) ---
        case "overlaps": {
          if (fieldType !== "array")
            throw new Error(`Operator '${operator}' is only for array fields.`);
          if (!isValueValid(value) || !isValueValid(value2)) {
            throw new Error(
              "Operator 'overlaps' requires two valid number values."
            );
          }

          // Assumes field is stored as [min, max]
          // Logic: storedMin <= value2 AND storedMax >= value
          queryParts.push({
            $and: [
              { [`${field}.0`]: { $lte: Number(value2) } },
              { [`${field}.1`]: { $gte: Number(value) } },
            ],
          });
          break;
        }

        case "includes_all": {
          if (fieldType !== "array")
            throw new Error(`Operator '${operator}' is only for array fields.`);
          const validValues = values.filter(isValueValid);
          if (validValues.length === 0)
            throw new Error(
              `Operator '${operator}' requires at least one valid value.`
            );
          // Logic: The array field contains ALL of these values
          queryParts.push({ [field]: { $all: validValues } });
          break;
        }

        case "excludes_all": {
          if (fieldType !== "array")
            throw new Error(`Operator '${operator}' is only for array fields.`);
          const validValues = values.filter(isValueValid);
          if (validValues.length === 0)
            throw new Error(
              `Operator '${operator}' requires at least one valid value.`
            );
          // Logic: The array field does NOT contain ALL of these values
          queryParts.push({ [field]: { $not: { $all: validValues } } });
          break;
        }

        // --- Text / Email / URL / Tel Operators ---
        case "is_not": {
          if (fieldType === "date") {
            if (!isValueValid(value))
              throw new Error("A valid date value is required.");

            const startDate = new Date(value);
            startDate.setHours(0, 0, 0, 0);
            const endDate = new Date(value);
            endDate.setHours(23, 59, 59, 999);

            if (isNaN(startDate.getTime()))
              throw new Error("Invalid date format provided.");

            // Logic: "is before the start of the day OR after the end of the day"
            queryParts.push({
              $or: [
                { [field]: { $lt: startDate } },
                { [field]: { $gt: endDate } },
              ],
            });
          } else {
            queryParts.push({ [field]: { $ne: value } });
          }
          break;
          break;
        }
        case "contains": {
          if (!isValueValid(value))
            throw new Error(`Operator '${operator}' requires a valid value.`);

          if (fieldType === "array") {
            // For 'numberrange' type
            // Assumes field is stored as [min, max]
            // Logic: storedMin <= value AND storedMax >= value
            queryParts.push({
              $and: [
                { [`${field}.0`]: { $lte: Number(value) } },
                { [`${field}.1`]: { $gte: Number(value) } },
              ],
            });
          } else {
            queryParts.push({
              [field]: { $regex: new RegExp(escapeRegExp(value), "i") },
            });
          }
          break;
        }
        case "not_contains": {
          if (!isValueValid(value))
            throw new Error(`Operator '${operator}' requires a valid value.`);

          queryParts.push({
            [field]: {
              $not: { $regex: new RegExp(escapeRegExp(String(value)), "i") },
            },
          });
          break;
        }
        case "starts_with": {
          if (!isValueValid(value))
            throw new Error(`Operator '${operator}' requires a valid value.`);

          queryParts.push({
            [field]: {
              $regex: new RegExp("^" + escapeRegExp(String(value)), "i"),
            },
          });
          break;
        }
        case "ends_with": {
          if (!isValueValid(value))
            throw new Error(`Operator '${operator}' requires a valid value.`);

          queryParts.push({
            [field]: {
              $regex: new RegExp(escapeRegExp(String(value)) + "$", "i"),
            },
          });
          break;
        }

        // --- Number Operators ---
        case "equals": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid number value.`
            );

          queryParts.push({ [field]: { $eq: Number(value) } });
          break;
        }
        case "not_equals": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid number value.`
            );

          queryParts.push({ [field]: { $ne: Number(value) } });
          break;
        }
        case "greater_than": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid number value.`
            );

          queryParts.push({ [field]: { $gt: Number(value) } });
          break;
        }
        case "less_than": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid number value.`
            );

          queryParts.push({ [field]: { $lt: Number(value) } });
          break;
        }

        // --- Date / Datetime Operators ---
        case "before": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid date value.`
            );

          queryParts.push({ [field]: { $lt: new Date(value) } });
          break;
        }

        case "after": {
          if (!isValueValid(value))
            throw new Error(
              `Operator '${operator}' requires a valid date value.`
            );

          queryParts.push({ [field]: { $gt: new Date(value) } });
          break;
        }

        // --- Select / Multiselect Operators ---
        case "is_any_of": {
          const validValues = values.filter(isValueValid);
          if (validValues.length === 0)
            throw new Error(
              `Operator '${operator}' requires at least one valid value.`
            );
          queryParts.push({ [field]: { $in: validValues } });
          break;
        }
        case "is_not_any_of": {
          const validValues = values.filter(isValueValid);
          if (validValues.length === 0)
            throw new Error(
              `Operator '${operator}' requires at least one valid value.`
            );
          queryParts.push({ [field]: { $nin: validValues } });
          break;
        }

        // --- Empty / Not Empty (Works for all types) ---
        case "empty": {
          if (fieldType === "string") {
            queryParts.push({ [field]: { $in: [null, undefined, ""] } });
          } else {
            queryParts.push({ [field]: { $in: [null, undefined] } });
          }
          break;
        }

        case "not_empty": {
          if (fieldType === "string") {
            queryParts.push({ [field]: { $nin: [null, undefined, ""] } });
          } else {
            queryParts.push({ [field]: { $nin: [null, undefined] } });
          }
          break;
        }

        default:
          throw new InvalidFilterError(`Unknown filter operator: ${operator}`);
      }
    } catch (error: any) {
      return {
        query: null,
        error: new InvalidFilterError(
          `Invalid filter for field '${field}' (operator '${operator}'): ${error.message}`
        ),
      };
    }
  }

  if (queryParts.length === 0) {
    return { query: {}, error: null };
  }

  return {
    query: { $and: queryParts },
    error: null,
  };
};
