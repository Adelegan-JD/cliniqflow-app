import React from 'react'
import { useNurseStore } from '../../store/nurseSttore'
import { useEffect } from 'react'

export const NurseDashboard = () => {
  
  const { health, isLoading, gethealthStatus} = useNurseStore()

  useEffect(() => {
    gethealthStatus()
  }, [])

  return (
    <div>
      <h1 className='text-2xl font-bold mb-4'>Nurse Dashboard</h1>
      {isLoading ? (
        <p>Loading health status...</p>
      ) : (
        <p>Health Status: {health?.status || 'N/A'}</p>
      )}

    </div>
  )
}
