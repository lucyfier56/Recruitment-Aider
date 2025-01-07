'use client'

import { useState } from 'react'
import JDsTable from '@/components/JDsTable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Search } from 'lucide-react'
import { JDDialog } from '@/components/JDDialog'

export default function JDsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold tracking-tight">Job Descriptions</h1>
        <div className="flex space-x-2">
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
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Create JD
          </Button>
        </div>
      </div>
      <JDsTable searchQuery={searchQuery} />
      <JDDialog open={dialogOpen} onOpenChange={setDialogOpen} jd={null} />
    </div>
  )
}

