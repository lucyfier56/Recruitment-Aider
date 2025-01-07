'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function AddApplicationModal({ open, onOpenChange, selectedJD }) {
  const [files, setFiles] = useState([])

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Submitting applications:', { selectedJD, files })
    // Implement the logic to handle the file uploads here
    onOpenChange(false)
  }

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Applications for {selectedJD?.title}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="resumes">Upload Resumes</Label>
            <Input
              id="resumes"
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
            />
          </div>
          <DialogFooter>
            <Button type="submit">Upload Applications</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

