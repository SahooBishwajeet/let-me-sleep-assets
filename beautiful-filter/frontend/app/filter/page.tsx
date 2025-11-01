"use client";

import { Button } from "@/components/ui/button";
import {
  Filters,
  type Filter,
  type FilterFieldConfig,
} from "@/components/ui/filters";
import axios from "axios";
import { AlertCircle, Calendar, FunnelX, Mail, Star, User } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

// --- Interfaces ---

interface IResponse {
  data: IData[];
  message: string;
}

interface IData {
  id: string;
  name: string;
  email: string;
  dateOfBirth?: string;
  score?: number;
  isPriority?: boolean;
  createdAt: string;
  updatedAt: string;
}

// --- Filter Configuration ---

const names = [
  "John Doe",
  "Alice Smith",
  "Bob Lee",
  "Nina Brown",
  "Eve Adams",
  "Tom Chen",
  "Lara Patel",
];

const fields: FilterFieldConfig[] = [
  {
    key: "name",
    label: "Name",
    icon: <User className="size-3.5" />,
    type: "multiselect",
    className: "w-[200px]",
    options: names.map((name) => ({
      value: name,
      label: name,
    })),
  },
  {
    key: "email",
    label: "Email",
    icon: <Mail className="size-3.5" />,
    type: "email",
    className: "w-48",
    placeholder: "user@example.com",
  },
  {
    key: "dateOfBirth",
    label: "Date of Birth",
    icon: <Calendar className="size-3.5" />,
    type: "date",
    className: "w-36",
  },
  {
    key: "score",
    label: "Score",
    icon: <Star className="size-3.5" />,
    type: "number",
    min: 0,
    max: 100,
    step: 1,
  },
  {
    key: "isPriority",
    label: "Is Priority",
    icon: <AlertCircle className="size-3.5" />,
    type: "boolean",
  },
  {
    key: "createdAt",
    label: "Created At",
    icon: <Calendar className="size-3.5" />,
    type: "date",
    className: "w-36",
  },
  {
    key: "updatedAt",
    label: "Updated At",
    icon: <Calendar className="size-3.5" />,
    type: "date",
    className: "w-36",
  },
];

export default function Home() {
  const [data, setData] = useState<IData[]>([]);
  const [loading, setLoading] = useState<boolean>(true); // Start loading
  const [error, setError] = useState<string>("");
  const [filters, setFilters] = useState<Filter[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");

        const URL = "http://localhost:3000/api/data/filter";
        const response = await axios.post<IResponse>(URL, { filters });

        setData(response.data.data);
      } catch (err) {
        setError("Failed to fetch data");
        console.error("Fetch Error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [filters]);

  const handleFiltersChange = useCallback((newFilters: Filter[]) => {
    setFilters(newFilters);
  }, []);

  const RenderContent = () => {
    if (loading) {
      return <p>Loading...</p>;
    }

    if (error) {
      return <p style={{ color: "red" }}>{error}</p>;
    }

    if (data.length === 0) {
      return <p>No data available</p>;
    }

    return (
      <table className="w-full">
        <thead>
          <tr className="text-lg">
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Date of Birth</th>
            <th>Score</th>
            <th>Priority</th>
            <th>Created Date</th>
            <th>Updated Date</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.id} className="p-2 border-b border-white/40">
              <td>{item.id}</td>
              <td>{item.name}</td>
              <td>{item.email}</td>
              <td>
                {item.dateOfBirth
                  ? new Date(item.dateOfBirth).toLocaleDateString()
                  : "N/A"}
              </td>
              <td>{item.score !== undefined ? item.score : "N/A"}</td>
              <td>{item.isPriority === undefined ? "N/A" : item.isPriority ? "Yes" : "No"}</td>
              <td>{new Date(item.createdAt).toLocaleString()}</td>
              <td>{new Date(item.updatedAt).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="space-y-5">
      <h1 className="text-4xl">Beautiful Filter</h1>

      {/* Filters Section */}
      <div className="flex items-start gap-2.5">
        <div className="flex-1">
          <Filters
            filters={filters}
            fields={fields}
            variant="outline"
            onChange={handleFiltersChange}
          />
        </div>

        {filters.length > 0 && (
          <Button variant="outline" onClick={() => setFilters([])}>
            <FunnelX className="mr-2 size-4" /> Clear
          </Button>
        )}
      </div>

      {/* Data Table Section */}
      <RenderContent />
    </div>
  );
}
