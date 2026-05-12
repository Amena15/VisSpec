import React from 'react';

export const CardSkeleton = () => (
  <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)] animate-pulse">
    <div className="flex items-center">
      <div className="p-3 rounded-lg bg-gray-200 mr-4 w-12 h-12"></div>
      <div className="flex-1">
        <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
        <div className="h-8 bg-gray-200 rounded w-16"></div>
      </div>
    </div>
  </div>
);

export const TableRowSkeleton = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="flex items-center">
        <div className="w-5 h-5 bg-gray-200 rounded mr-3"></div>
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-32 mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-24"></div>
        </div>
      </div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-6 bg-gray-200 rounded-full w-16"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-12"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-16"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-8"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-16"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="flex space-x-3">
        <div className="h-4 bg-gray-200 rounded w-12"></div>
        <div className="h-4 bg-gray-200 rounded w-10"></div>
      </div>
    </td>
  </tr>
);

export const PredictionCardSkeleton = () => (
  <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden animate-pulse">
    <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
      <div className="h-6 bg-gray-200 rounded w-40"></div>
      <div className="h-10 bg-gray-200 rounded w-24"></div>
    </div>
    <div className="p-6">
      <div className="flex flex-col lg:flex-row gap-8">
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-48 h-48 bg-gray-200 rounded-full"></div>
        </div>
        <div className="flex-1 flex flex-col justify-center">
          <div className="mb-6">
            <div className="h-6 bg-gray-200 rounded w-48 mb-3"></div>
            <div className="h-20 bg-gray-200 rounded w-full"></div>
          </div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-32"></div>
            <div className="h-4 bg-gray-200 rounded w-36"></div>
            <div className="h-4 bg-gray-200 rounded w-32"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
);
