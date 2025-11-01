'use client';

import axios from "axios";
import { useEffect, useState } from "react";

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

export default function Home() {
  const [data, setData] = useState<IData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const URL = "http://localhost:3000/api/data";
      const response = await axios.get<IResponse>(URL);
      setData(response.data.data);
    } catch (err) {
      setError("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
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
                {item.dateOfBirth}
              </td>
              <td>{item.score !== undefined ? item.score : "N/A"}</td>
              <td>{item.isPriority === undefined ? "N/A" : item.isPriority ? "Yes" : "No"}</td>
              <td>{item.createdAt}</td>
              <td>{item.updatedAt}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div>
      <h1 className="text-4xl">Beautiful Filter</h1>
      <RenderContent />
    </div>
  );
}
