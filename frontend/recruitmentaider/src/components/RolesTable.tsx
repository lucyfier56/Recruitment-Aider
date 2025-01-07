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
import { Edit2, Trash2 } from 'lucide-react'
import { RoleDialog } from './RoleDialog'

// Mock data for roles
const mockRoles = [
  { id: 1, name: 'Software Engineer', department: 'Engineering', workType: 'Remote' },
  { id: 2, name: 'Product Manager', department: 'Product', workType: 'Hybrid' },
  { id: 3, name: 'UX Designer', department: 'Design', workType: 'On-site' },
  { id: 4, name: 'Data Analyst', department: 'Data Science', workType: 'Remote' },
  { id: 5, name: 'Marketing Specialist', department: 'Marketing', workType: 'Hybrid' },
  { id: 6, name: 'Sales Representative', department: 'Sales', workType: 'On-site' },
  { id: 7, name: 'HR Manager', department: 'Human Resources', workType: 'Hybrid' },
  { id: 8, name: 'Financial Analyst', department: 'Finance', workType: 'Remote' },
  { id: 9, name: 'Customer Support Specialist', department: 'Customer Service', workType: 'Remote' },
  { id: 10, name: 'Operations Manager', department: 'Operations', workType: 'On-site' },
  { id: 11, name: 'Quality Assurance Engineer', department: 'Engineering', workType: 'Hybrid' },
  { id: 12, name: 'Content Writer', department: 'Marketing', workType: 'Remote' },
]

export default function RolesTable({ searchQuery }) {
  const [page, setPage] = useState(1)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState(null)

  const itemsPerPage = 10

  const filteredRoles = useMemo(() => {
    return mockRoles.filter(role =>
      role.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      role.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      role.workType.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [searchQuery])

  const totalPages = Math.ceil(filteredRoles.length / itemsPerPage)

  const handleEdit = (role) => {
    setSelectedRole(role)
    setDialogOpen(true)
  }

  const handleDelete = (roleId) => {
    // Implement delete functionality
    console.log('Delete role:', roleId)
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Name</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Work Type</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredRoles
              .slice((page - 1) * itemsPerPage, page * itemsPerPage)
              .map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">{role.name}</TableCell>
                  <TableCell>{role.department}</TableCell>
                  <TableCell>{role.workType}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(role)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(role.id)}>
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
          Showing {Math.min(filteredRoles.length, page * itemsPerPage)} of {filteredRoles.length} results
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
      <RoleDialog open={dialogOpen} onOpenChange={setDialogOpen} role={selectedRole} />
    </div>
  )
}

