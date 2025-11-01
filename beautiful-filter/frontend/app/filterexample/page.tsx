'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Filters, type Filter, type FilterFieldConfig } from '@/components/ui/filters';
import {
  AlertCircle,
  Calendar,
  Check,
  Copy,
  FunnelX,
  Mail,
  Star,
  User
} from 'lucide-react';
import { useCallback, useState } from 'react';

// List of names for the name filter
const names = [
  "John Doe",
  "Alice Smith",
  "Bob Lee",
  "Nina Brown",
  "Eve Adams",
  "Tom Chen",
  "Lara Patel",
];

export default function FiltersDemo() {
  const fields: FilterFieldConfig[] = [
    {
      key: 'name',
      label: 'Name',
      icon: <User className="size-3.5" />,
      type: 'multiselect',
      className: 'w-[200px]',
      options: names.map(name => ({
        value: name,
        label: name,
        icon: (
          <Avatar className="size-5">
            <AvatarFallback>
              {name.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>
        ),
      })),
    },
    {
      key: 'email',
      label: 'Email',
      icon: <Mail className="size-3.5" />,
      type: 'email',
      className: 'w-48',
      placeholder: 'user@example.com',
    },
    {
      key: 'dateOfBirth',
      label: 'Date of Birth',
      icon: <Calendar className="size-3.5" />,
      type: 'date',
      className: 'w-36',
    },
    {
      key: 'score',
      label: 'Score',
      icon: <Star className="size-3.5" />,
      type: 'number',
      min: 0,
      max: 100,
      step: 1,
    },
    {
      key: 'isPriority',
      label: 'Is Priority',
      icon: <AlertCircle className="size-3.5" />,
      type: 'boolean',
    },
    {
      key: 'createdAt',
      label: 'Created At',
      icon: <Calendar className="size-3.5" />,
      type: 'date',
      className: 'w-36',
    },
    {
      key: 'updatedAt',
      label: 'Updated At',
      icon: <Calendar className="size-3.5" />,
      type: 'date',
      className: 'w-36',
    },
  ];

  const [filters, setFilters] = useState<Filter[]>([]);
  const [isCopied, setIsCopied] = useState(false);

  const handleFiltersChange = useCallback((filters: Filter[]) => {
    console.log('Filters updated:', filters);
    setFilters(filters);
  }, []);

  // Handle copy to clipboard
  const handleCopy = useCallback(() => {
    const jsonString = JSON.stringify(filters, null, 2);
    navigator.clipboard.writeText(jsonString).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  }, [filters]);

  return (
    <div className="flex items-start gap-2.5 grow self-start content-start">
      <div className="grow space-y-5">
        {/* Filters Section */}
        <div className="flex items-start gap-2.5">
          <div className="flex-1">
            <Filters filters={filters} fields={fields} variant="outline" onChange={handleFiltersChange} />
          </div>

          {filters.length > 0 && (
            <Button variant="outline" onClick={() => setFilters([])}>
              <FunnelX /> Clear
            </Button>
          )}
        </div>

        {/* Debug Block with Copy Button */}
        <div className="relative">
          <Button
            size="icon"
            variant="ghost"
            className="absolute top-2 right-2 h-7 w-7"
            onClick={handleCopy}
          >
            {isCopied ? (
              <Check className="size-3.5 text-green-500" />
            ) : (
              <Copy className="size-3.5" />
            )}
            <span className="sr-only">Copy to clipboard</span>
          </Button>

          <pre className="mt-2 p-3 bg-muted rounded-md border text-xs overflow-x-auto max-h-[400px] overflow-auto">
            {JSON.stringify(filters, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
