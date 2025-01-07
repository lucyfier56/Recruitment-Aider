'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Search, Plus } from 'lucide-react'
import ApplicationsTable from '@/components/ApplicationsTable'
import AddApplicationModal from '@/components/AddApplicationModal'

// Mock data for job descriptions
const mockJDs = [
  { id: 1, title: 'Senior Software Engineer', department: 'Engineering' },
  { id: 2, title: 'Product Manager', department: 'Product' },
  { id: 3, title: 'UX Designer', department: 'Design' },
  { id: 4, title: 'Data Scientist', department: 'Data Science' },
  { id: 5, title: 'Marketing Specialist', department: 'Marketing' },
]

export default function ApplicationsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedJD, setSelectedJD] = useState(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  const filteredJDs = mockJDs.filter(jd =>
    jd.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    jd.department.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold tracking-tight">Applications</h1>
        {!selectedJD && (
          <Button onClick={() => setIsAddModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Applications
          </Button>
        )}
      </div>
      {!selectedJD && (
        <>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search job descriptions..."
              className="pl-8 pr-4"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredJDs.map((jd) => (
              <Card key={jd.id} className="cursor-pointer hover:bg-gray-50" onClick={() => setSelectedJD(jd)}>
                <CardHeader>
                  <CardTitle>{jd.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500">{jd.department}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
      {selectedJD && (
        <ApplicationsTable 
          jd={selectedJD} 
          onBack={() => setSelectedJD(null)} 
          onAddApplications={() => setIsAddModalOpen(true)}
        />
      )}
      <AddApplicationModal 
        open={isAddModalOpen} 
        onOpenChange={setIsAddModalOpen} 
        selectedJD={selectedJD}
      />
    </div>
  )
}

