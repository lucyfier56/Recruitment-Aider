'use client'

import { useState, useMemo } from 'react'
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
import { Edit2, Trash2, FileText } from 'lucide-react'
import { JDDialog } from './JDDialog'

// Mock data for job descriptions
const mockJDs = [
  { id: 1, title: 'Senior Software Engineer', department: 'Engineering', location: 'Remote', status: 'active', fileType: 'manual' },
  { id: 2, title: 'Product Manager', department: 'Product', location: 'New York, NY', status: 'active', fileType: 'pdf' },
  { id: 3, title: 'UX Designer', department: 'Design', location: 'San Francisco, CA', status: 'processing', fileType: 'docx' },
  { id: 4, title: 'Data Scientist', department: 'Data Science', location: 'Remote', status: 'active', fileType: 'manual' },
  { id: 5, title: 'Marketing Specialist', department: 'Marketing', location: 'Chicago, IL', status: 'closed', fileType: 'pdf' },
]

export default function JDsTable({ searchQuery }) {
  const [page, setPage] = useState(1)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedJD, setSelectedJD] = useState(null)

  const itemsPerPage = 10

  const filteredJDs = useMemo(() => {
    return mockJDs.filter(jd =>
      jd.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      jd.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      jd.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      jd.status.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [searchQuery])

  const totalPages = Math.ceil(filteredJDs.length / itemsPerPage)

  const handleEdit = (jd) => {
    setSelectedJD(jd)
    setDialogOpen(true)
  }

  const handleDelete = (jdId) => {
    // Implement delete functionality
    console.log('Delete JD:', jdId)
  }

  const getStatusBadge = (status) => {
    const statusColors = {
      processing: 'bg-yellow-500',
      active: 'bg-green-500',
      closed: 'bg-gray-500',
    }
    return <Badge className={`${statusColors[status]} text-white`}>{status}</Badge>
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Title</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredJDs
              .slice((page - 1) * itemsPerPage, page * itemsPerPage)
              .map((jd) => (
                <TableRow key={jd.id}>
                  <TableCell className="font-medium">{jd.title}</TableCell>
                  <TableCell>{jd.department}</TableCell>
                  <TableCell>{jd.location}</TableCell>
                  <TableCell>{getStatusBadge(jd.status)}</TableCell>
                  <TableCell>
                    {jd.fileType === 'manual' ? (
                      <span>Form</span>
                    ) : (
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <FileText className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(jd)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(jd.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Showing {Math.min(filteredJDs.length, page * itemsPerPage)} of {filteredJDs.length} results
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
      <JDDialog open={dialogOpen} onOpenChange={setDialogOpen} jd={selectedJD} />
    </div>
  )
}

