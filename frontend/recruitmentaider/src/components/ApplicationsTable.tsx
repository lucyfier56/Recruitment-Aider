'use client'

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, FileText, Plus } from 'lucide-react'
import AnalysisModal from './AnalysisModal'

// Mock data for applications
const mockApplications = [
  { id: 1, name: 'John Doe', email: 'john@example.com', status: 'processing', resumeFile: 'john-doe-resume.pdf' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'finished', resumeFile: 'jane-smith-resume.pdf' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'processing', resumeFile: 'bob-johnson-resume.pdf' },
  { id: 4, name: 'Alice Brown', email: 'alice@example.com', status: 'finished', resumeFile: 'alice-brown-resume.pdf' },
  { id: 5, name: 'Charlie Davis', email: 'charlie@example.com', status: 'processing', resumeFile: 'charlie-davis-resume.pdf' },
]

export default function ApplicationsTable({ jd, onBack, onAddApplications }) {
  const [page, setPage] = useState(1)
  const itemsPerPage = 10
  const totalPages = Math.ceil(mockApplications.length / itemsPerPage)
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false)
  const [selectedApplication, setSelectedApplication] = useState(null)

  const getStatusBadge = (status) => {
    const statusColors = {
      processing: 'bg-yellow-500',
      finished: 'bg-green-500',
    }
    return <Badge className={`${statusColors[status]} text-white`}>{status}</Badge>
  }

  const handleOpenAnalysis = (application) => {
    setSelectedApplication(application)
    setIsAnalysisModalOpen(true)
  }

  return (
    <div className="space-y-4 w-full">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Button variant="ghost" onClick={onBack}>
            <ChevronLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <h2 className="text-xl font-semibold">{jd.title} - Applications</h2>
        </div>
        <Button onClick={onAddApplications}>
          <Plus className="mr-2 h-4 w-4" /> Add Applications
        </Button>
      </div>
      <div className="rounded-md border w-full">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Resume</TableHead>
              <TableHead>Analysis</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockApplications
              .slice((page - 1) * itemsPerPage, page * itemsPerPage)
              .map((application) => (
                <TableRow key={application.id}>
                  <TableCell className="font-medium">{application.name}</TableCell>
                  <TableCell>{application.email}</TableCell>
                  <TableCell>{getStatusBadge(application.status)}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <FileText className="h-4 w-4" />
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={() => handleOpenAnalysis(application)}>
                      Analysis
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Showing {Math.min(mockApplications.length, page * itemsPerPage)} of {mockApplications.length} results
        </p>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
          >
            Next
          </Button>
        </div>
      </div>
      <AnalysisModal
        open={isAnalysisModalOpen}
        onOpenChange={setIsAnalysisModalOpen}
        application={selectedApplication}
      />
    </div>
  )
}

